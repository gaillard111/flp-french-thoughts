<?php

/**
 * This file is part of the <name> project.
 *
 * (c) <yourname> <youremail>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Application\Sonata\UserBundle\Entity;

use Doctrine\ORM\Mapping as ORM;
use Sonata\UserBundle\Entity\BaseUser as BaseUser;
use Symfony\Component\Validator\Constraints as Assert;

/**
 * @ORM\Entity
 * @ORM\HasLifecycleCallbacks()
 */
class User extends BaseUser
{
    /**
     * @var int $id
     */
    protected $id;

    /**
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\Thought", mappedBy="owner")
     */
    protected $thoughts;

    /**
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\Chain", mappedBy="user")
     */
    protected $chains;

    /**
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\ChainComment", mappedBy="user")
     */
    protected $chainComments;

    /**
     * @Assert\NotBlank(groups={"profileInfo"}, message = "user.about.not_blank")
     */
    protected $about;

    /**
     * @Assert\NotBlank(groups={"profileInfo"}, message = "user.country.not_blank")
     */
    protected $country;

    /**
     * @Assert\NotBlank(groups={"profileInfo"}, message = "user.interests.not_blank")
     */
    protected $interests;

    /**
     * @Assert\NotBlank(groups={"CustomProfile"})
     */
    protected $firstname;

    /**
     * @Assert\NotBlank(groups={"CustomProfile"})
     */
    protected $lastname;

    /**
     * @Assert\NotBlank(groups={"profileInfo"}, message="user.gender.not_blank")
     */
    protected $gender;

    /**
     * Get id
     *
     * @return int $id
     */
    public function getId()
    {
        return $this->id;
    }

    /**
     * Add thoughts
     *
     * @param \ThoughtBundle\Entity\Thought $thoughts
     * @return User
     */
    public function addThought(\ThoughtBundle\Entity\Thought $thoughts)
    {
        $this->thoughts[] = $thoughts;

        return $this;
    }

    /**
     * Remove thoughts
     *
     * @param \ThoughtBundle\Entity\Thought $thoughts
     */
    public function removeThought(\ThoughtBundle\Entity\Thought $thoughts)
    {
        $this->thoughts->removeElement($thoughts);
    }

    /**
     * Get thoughts
     *
     * @return \Doctrine\Common\Collections\Collection
     */
    public function getThoughts()
    {
        return $this->thoughts;
    }

    /**
     * @inheritdoc
     */
    public function prePersist()
    {
        parent::prePersist();
        $this->username = $this->email;
    }

    /**
     * @inheritdoc
     */
    public function preUpdate()
    {
        parent::preUpdate();
        $this->username = $this->email;
    }

    /**
     * Add chains
     *
     * @param \ThoughtBundle\Entity\Chain $chains
     * @return User
     */
    public function addChain(\ThoughtBundle\Entity\Chain $chains)
    {
        $this->chains[] = $chains;

        return $this;
    }

    /**
     * Remove chains
     *
     * @param \ThoughtBundle\Entity\Chain $chains
     */
    public function removeChain(\ThoughtBundle\Entity\Chain $chains)
    {
        $this->chains->removeElement($chains);
    }

    /**
     * Get chains
     *
     * @return \Doctrine\Common\Collections\Collection 
     */
    public function getChains()
    {
        return $this->chains;
    }

    /**
     * Add chainComments
     *
     * @param \ThoughtBundle\Entity\ChainComment $chainComments
     * @return User
     */
    public function addChainComment(\ThoughtBundle\Entity\ChainComment $chainComments)
    {
        $this->chainComments[] = $chainComments;

        return $this;
    }

    /**
     * Remove chainComments
     *
     * @param \ThoughtBundle\Entity\ChainComment $chainComments
     */
    public function removeChainComment(\ThoughtBundle\Entity\ChainComment $chainComments)
    {
        $this->chainComments->removeElement($chainComments);
    }

    /**
     * Get chainComments
     *
     * @return \Doctrine\Common\Collections\Collection 
     */
    public function getChainComments()
    {
        return $this->chainComments;
    }

    /**
     * Get fullName + email
     *
     * @return string
     */
    public function getFullNameEmail()
    {
        $fullName = trim(parent::getFullname());

        return  (!empty($fullName) ? $fullName . ', ' : '') . $this->getEmail();
    }

    /**
     * Set about
     *
     * @param string $about
     * @return User
     */
    public function setAbout($about)
    {
        $this->about = $about;

        return $this;
    }

    /**
     * Get about
     *
     * @return string 
     */
    public function getAbout()
    {
        return $this->about;
    }

    /**
     * Set country
     *
     * @param string $country
     * @return User
     */
    public function setCountry($country)
    {
        $this->country = $country;

        return $this;
    }

    /**
     * Get country
     *
     * @return string 
     */
    public function getCountry()
    {
        return $this->country;
    }

    /**
     * Set interests
     *
     * @param string $interests
     * @return User
     */
    public function setInterests($interests)
    {
        $this->interests = $interests;

        return $this;
    }

    /**
     * Get interests
     *
     * @return string 
     */
    public function getInterests()
    {
        return $this->interests;
    }
}
