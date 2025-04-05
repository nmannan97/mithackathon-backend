use anchor_lang::prelude::*;
use anchor_spl::token::{self, Mint, Token, TokenAccount, Transfer, MintTo};

declare_id!("5yygEnW3bWU7F477pP9CKAfB5yh2bZEgjdedyFqi7CPB");

#[program]
pub mod fundraising_campaign {
    use super::*;

    // Initializes the fundraising campaign with a goal and token mint
    pub fn initialize_campaign(
        ctx: Context<InitializeCampaign>,
        goal: u64,
        token_mint: Pubkey,
    ) -> Result<()> {
        let campaign = &mut ctx.accounts.campaign;
        campaign.creator = *ctx.accounts.creator.key;
        campaign.goal = goal;
        campaign.raised = 0;
        campaign.token_mint = token_mint;
        Ok(())
    }

    // Allows an investor to invest a specific amount
    pub fn invest(ctx: Context<Invest>, amount: u64) -> Result<()> {
        // Transfer the investment (USDC or other token) from the investor to the vault
        token::transfer(
            ctx.accounts
                .into_transfer_to_vault_context()
                .with_signer(&[]),
            amount,
        )?;

        // Mint new equity tokens to the investor based on their investment
        token::mint_to(
            ctx.accounts
                .into_mint_to_investor_context()
                .with_signer(&[]),
            amount,
        )?;

        // Update the total amount raised in the campaign
        let campaign = &mut ctx.accounts.campaign;
        campaign.raised += amount;
        Ok(())
    }
}

// Define the context for initializing the campaign
#[derive(Accounts)]
pub struct InitializeCampaign<'info> {
    #[account(init, payer = creator, space = 8 + 32 + 8 + 8 + 32)]
    pub campaign: Account<'info, Campaign>,
    #[account(mut)]
    pub creator: Signer<'info>,
    pub system_program: Program<'info, System>,
}

// Define the context for an investor to make an investment
#[derive(Accounts)]
pub struct Invest<'info> {
    #[account(mut)]
    pub campaign: Account<'info, Campaign>,
    #[account(mut)]
    pub investor: Signer<'info>,
    #[account(mut)]
    pub investor_token_account: Account<'info, TokenAccount>,
    #[account(mut)]
    pub vault_token_account: Account<'info, TokenAccount>,
    pub token_program: Program<'info, Token>,
}

// Define the data structure for the campaign
#[account]
pub struct Campaign {
    pub creator: Pubkey,
    pub goal: u64,
    pub raised: u64,
    pub token_mint: Pubkey,
}

// Implement helper methods for the 'Invest' context to transfer tokens and mint new tokens
impl<'info> Invest<'info> {
    // Create the context for transferring tokens from the investor to the vault
    fn into_transfer_to_vault_context(&self) -> CpiContext<'_, '_, '_, 'info, Transfer<'info>> {
        CpiContext::new(
            self.token_program.to_account_info(),
            Transfer {
                from: self.investor_token_account.to_account_info(),
                to: self.vault_token_account.to_account_info(),
                authority: self.investor.to_account_info(),
            },
        )
    }

    // Create the context for minting new tokens for the investor
    fn into_mint_to_investor_context(&self) -> CpiContext<'_, '_, '_, 'info, MintTo<'info>> {
        CpiContext::new(
            self.token_program.to_account_info(),
            MintTo {
                mint: self.campaign.token_mint.to_account_info(),
                to: self.investor_token_account.to_account_info(),
                authority: self.campaign.to_account_info(),
            },
        )
    }
}