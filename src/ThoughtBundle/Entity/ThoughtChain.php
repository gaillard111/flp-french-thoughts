<?php

namespace ThoughtBundle\Entity;

use Doctrine\ORM\Mapping as ORM;

/**
 * Class ThoughtChain
 *
 * @ORM\Entity(repositoryClass="ThoughtBundle\Repository\ThoughtChainRepository")
 * @ORM\Table(name="thought_chain")
 * @ORM\HasLifecycleCallbacks()
 */
class ThoughtChain
{
    /**
     * @ORM\Id
     * @ORM\Column(type="integer")
     * @ORM\GeneratedValue(strategy="AUTO")
     */
    protected $id;

    /**
     * @ORM\ManyToOne(targetEntity="ThoughtBundle\Entity\Chain", inversedBy="chainThoughts")
     * @ORM\JoinColumn(name="chain_id", referencedColumnName="id")
     */
    protected $chain;

    /**
     * @ORM\ManyToOne(targetEntity="ThoughtBundle\Entity\Thought", inversedBy="chainThoughts")
     * @ORM\JoinColumn(name="thought_id", referencedColumnName="id")
     */
    protected $thought;

    /**
     * @ORM\Column(name="sort_index", type="smallint")
     */
    protected $sortIndex = 0;

    /**
     * Get id
     *
     * @return integer 
     */
    public function getId()
    {
        return $this->id;
    }

    /**
     * Set sortIndex
     *
     * @param integer $sortIndex
     * @return ThoughtChain
     */
    public function setSortIndex($sortIndex)
    {
        $this->sortIndex = $sortIndex;

        return $this;
    }

    /**
     * Get sortIndex
     *
     * @return integer 
     */
    public function getSortIndex()
    {
        return $this->sortIndex;
    }

    /**
     * Set chain
     *
     * @param \ThoughtBundle\Entity\Chain $chain
     * @return ThoughtChain
     */
    public function setChain(\ThoughtBundle\Entity\Chain $chain = null)
    {
        $this->chain = $chain;

        return $this;
    }

    /**
     * Get chain
     *
     * @return \ThoughtBundle\Entity\Chain 
     */
    public function getChain()
    {
        return $this->chain;
    }

    /**
     * Set thought
     *
     * @param \ThoughtBundle\Entity\Thought $thought
     * @return ThoughtChain
     */
    public function setThought(\ThoughtBundle\Entity\Thought $thought = null)
    {
        $this->thought = $thought;

        return $this;
    }

    /**
     * Get thought
     *
     * @return \ThoughtBundle\Entity\Thought 
     */
    public function getThought()
    {
        return $this->thought;
    }
}
